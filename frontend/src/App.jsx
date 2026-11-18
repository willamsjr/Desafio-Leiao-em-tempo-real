
import { useEffect, useRef, useState } from "react";
import "./App.css";

function App() {
  const [itens, setItens] = useState([]);
  const [itemSelecionado, setItemSelecionado] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [erroHistorico, setErroHistorico] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(true);
  const [agora, setAgora] = useState(Date.now());
  const [participante, setParticipante] = useState("");
  const [valorLance, setValorLance] = useState("");
  const [erroLance, setErroLance] = useState("");
  const [enviando, setEnviando] = useState(false);
  const ultimoLanceIdRef = useRef({});
  const deslocamentoRelogioRef = useRef(0);
  const [conectado, setConectado] = useState(false);

  const [mostrarCadastro, setMostrarCadastro] = useState(false);
  const [novoItem, setNovoItem] = useState({
    nome: "",
    lance_minimo: "",
    encerra_em: "",
  });
  const [erroCadastro, setErroCadastro] = useState("");
  const [salvandoCadastro, setSalvandoCadastro] = useState(false);


  useEffect(() => {
    fetch("http://127.0.0.1:8000/itens")
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Erro ao consultar os leilões");
        }
        return resposta.json();
      })
      .then((dados) => setItens(dados))
      .catch((erro) => setErro(erro.message))
      .finally(() => setCarregando(false));
  }, []);

  const itemId = itemSelecionado?.id;

  useEffect(() => {
    if (!itemId) {
      setHistorico([]);
      return;
    }

    setErroHistorico("");

    fetch(`http://127.0.0.1:8000/itens/${itemId}/lances`)
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Erro ao carregar o histórico");
        }
        return resposta.json();
      })
      .then((dados) =>
        setHistorico((anteriores) => {
          const lances = new Map();

          [...dados, ...anteriores].forEach((lance) => {
            lances.set(lance.id, lance);
          });

          return [...lances.values()].sort((a, b) => a.id - b.id);
        })
      )
      .catch((erro) => setErroHistorico(erro.message));
  }, [itemId]);



  useEffect(() => {
    if (!itemId) return;

    setConectado(false);

    let ativo = true;
    let socket;
    let timerReconexao;

    async function sincronizar(conexao) {
      try {
        const respostaHistorico = await fetch(
          `http://127.0.0.1:8000/itens/${itemId}/lances`
        );

        if (!respostaHistorico.ok) {
          throw new Error("Erro ao sincronizar o histórico");
        }

        const dadosHistorico = await respostaHistorico.json();

        const respostaItens = await fetch(
          "http://127.0.0.1:8000/itens"
        );

        if (!respostaItens.ok) {
          throw new Error("Erro ao sincronizar o leilão");
        }

        const dadosItens = await respostaItens.json();

        if (
          !ativo ||
          socket !== conexao ||
          conexao.readyState !== WebSocket.OPEN
        ) return;

        const maiorIdBanco = dadosHistorico.reduce(
          (maior, lance) => Math.max(maior, lance.id),
          0
        );

        const ultimoId = ultimoLanceIdRef.current[itemId] ?? 0;
        const itemAtualizado = dadosItens.find(
          (item) => item.id === itemId
        );

        if (itemAtualizado && maiorIdBanco >= ultimoId) {
          ultimoLanceIdRef.current[itemId] = maiorIdBanco;

          setItemSelecionado((atual) =>
            atual?.id === itemId ? itemAtualizado : atual
          );

          setItens((anteriores) =>
            anteriores.map((item) =>
              item.id === itemId ? itemAtualizado : item
            )
          );
        }

        setHistorico((anteriores) => {
          const lances = new Map();

          [...dadosHistorico, ...anteriores].forEach((lance) => {
            lances.set(lance.id, lance);
          });

          return [...lances.values()].sort(
            (a, b) => a.id - b.id
          );
        });

        setErroHistorico("");
      } catch (erro) {
        if (ativo && socket === conexao) {
          setErroHistorico(erro.message);
        }
      }
    }

    function conectar() {
      const conexao = new WebSocket(
        `ws://127.0.0.1:8000/ws/itens/${itemId}`
      );

      socket = conexao;

      conexao.onopen = () => {
        if (ativo) {
          setConectado(true);
          sincronizar(conexao);
        }
      };

      conexao.onmessage = (evento) => {
        if (!ativo) return;

        const mensagem = JSON.parse(evento.data);

        if (mensagem.tipo === "conectado") {
          deslocamentoRelogioRef.current =
            new Date(mensagem.agora).getTime() - Date.now();

          setAgora(Date.now() + deslocamentoRelogioRef.current);
          return;
        }

        if (mensagem.tipo !== "novo_lance") return;

        const ultimoId = ultimoLanceIdRef.current[itemId] ?? 0;

        if (mensagem.lance.id > ultimoId) {
          ultimoLanceIdRef.current[itemId] = mensagem.lance.id;

          setItemSelecionado((atual) =>
            atual?.id === itemId ? mensagem.item : atual
          );

          setItens((anteriores) =>
            anteriores.map((item) =>
              item.id === itemId ? mensagem.item : item
            )
          );
        }

        setHistorico((anteriores) => {
          const lances = new Map(
            anteriores.map((lance) => [lance.id, lance])
          );

          lances.set(mensagem.lance.id, mensagem.lance);

          return [...lances.values()].sort(
            (a, b) => a.id - b.id
          );
        });
      };

      conexao.onclose = () => {
        if (ativo) {
          setConectado(false);
          timerReconexao = setTimeout(conectar, 2000);
        }
      };

      conexao.onerror = () => conexao.close();
    }

    conectar();

    return () => {
      ativo = false;
      clearTimeout(timerReconexao);
      socket?.close();
    };
  }, [itemId]);



  const dinheiro = (valor) =>
    Number(valor).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });

  useEffect(() => {
    const intervalo = setInterval(() => {
      setAgora(Date.now() + deslocamentoRelogioRef.current);
    }, 1000);

    return () => clearInterval(intervalo);
  }, []);

  const formatarTempoRestante = (encerramento) => {
    const diferenca = new Date(encerramento).getTime() - agora;

    if (diferenca <= 0) return "Leilão encerrado";

    const segundos = Math.ceil(diferenca / 1000);

    const dias = Math.floor(segundos / 86400);
    const horas = Math.floor((segundos % 86400) / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const seg = segundos % 60;

    return `${dias}d ${String(horas).padStart(2, "0")}h ${String(minutos).padStart(2, "0")}m ${String(seg).padStart(2, "0")}s`;
  };

  async function enviarLance(evento) {
    evento.preventDefault();
    if (!itemSelecionado || enviando) return;

    setEnviando(true);
    setErroLance("");

    try {
      const resposta = await fetch(
        `http://127.0.0.1:8000/itens/${itemSelecionado.id}/lances`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            participante,
            valor: valorLance,
          }),
        }
      );

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(
          typeof dados.detail === "string"
            ? dados.detail
            : "Não foi possível registrar o lance"
        );
      }

      const ultimoId =
        ultimoLanceIdRef.current[dados.item.id] ?? 0;

      if (dados.lance.id > ultimoId) {
        ultimoLanceIdRef.current[dados.item.id] = dados.lance.id;

        setItemSelecionado((atual) =>
          atual?.id === dados.item.id ? dados.item : atual
        );

        setItens((anteriores) =>
          anteriores.map((item) =>
            item.id === dados.item.id ? dados.item : item
          )
        );
      }

      setHistorico((anteriores) => {
        const lances = new Map(
          anteriores.map((lance) => [lance.id, lance])
        );

        lances.set(dados.lance.id, dados.lance);

        return [...lances.values()].sort(
          (a, b) => a.id - b.id
        );
      });
      setValorLance("");
    } catch (erro) {
      setErroLance(erro.message);
    } finally {
      setEnviando(false);
    }
  }


  async function cadastrarItem(evento) {
    evento.preventDefault();

    if (salvandoCadastro) return;

    const encerramento = new Date(novoItem.encerra_em);

    if (
      Number.isNaN(encerramento.getTime()) ||
      encerramento.getTime() <= Date.now()
    ) {
      setErroCadastro("O encerramento deve estar no futuro.");
      return;
    }

    setSalvandoCadastro(true);
    setErroCadastro("");

    try {
      const resposta = await fetch("http://127.0.0.1:8000/itens", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nome: novoItem.nome.trim(),
          lance_minimo: novoItem.lance_minimo,
          encerra_em: encerramento.toISOString(),
        }),
      });

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(
          typeof dados.detail === "string"
            ? dados.detail
            : "Erro ao cadastrar leilão."
        );
      }

      setItens((anteriores) => [...anteriores, dados]);

      setNovoItem({
        nome: "",
        lance_minimo: "",
        encerra_em: "",
      });

      setMostrarCadastro(false);
    } catch (erro) {
      setErroCadastro(erro.message);
    } finally {
      setSalvandoCadastro(false);
    }
  }


  // Sala do leilão

  if (itemSelecionado) {
    const encerrado =
      agora >= new Date(itemSelecionado.encerra_em).getTime();

    return (
      <main className="pagina">
        <button onClick={() => setItemSelecionado(null)}>
          ← Voltar aos leilões
        </button>

        <div className="sala-leilao">
          <h1>{itemSelecionado.nome}</h1>

          <p className={`estado-conexao ${conectado ? "online" : "offline"}`}>
            <span className="ponto-conexao"></span>
            {conectado ? "Conectado em tempo real" : "Reconectando..."}
          </p>

          <p>Lance mínimo: {dinheiro(itemSelecionado.lance_minimo)}</p>

          <h2>
            Lance atual:{" "}
            {itemSelecionado.lance_atual === null
              ? "Nenhum lance"
              : dinheiro(itemSelecionado.lance_atual)}
          </h2>

          <p>
            Encerramento:{" "}
            {new Date(itemSelecionado.encerra_em).toLocaleString("pt-BR")}
          </p>

          <div className="cronometro">
            <p>Tempo restante</p>
            <h2>
              {formatarTempoRestante(itemSelecionado.encerra_em)}
            </h2>
          </div>

          {!encerrado && (
            <div className="formulario-lance">
              <h3>Fazer um lance</h3>

              <form onSubmit={enviarLance}>
                <input
                  type="text"
                  placeholder="Seu nome"
                  value={participante}
                  onChange={(e) => setParticipante(e.target.value)}
                  required
                />

                <input
                  type="number"
                  placeholder="Valor do lance (R$)"
                  step="0.01"
                  min="0.01"
                  value={valorLance}
                  onChange={(e) => setValorLance(e.target.value)}
                  required
                />

                <button type="submit" disabled={enviando}>
                  {enviando ? "Enviando..." : "Enviar lance"}
                </button>
              </form>

              {erroLance && (
                <p className="erro-lance">{erroLance}</p>
              )}
            </div>
          )}

          {encerrado && (
            <p>Este leilão foi encerrado e não aceita novos lances.</p>
          )}

          <h3>Histórico de lances</h3>

          {erroHistorico && <p>{erroHistorico}</p>}

          {historico.length === 0 && !erroHistorico && (
            <p>Nenhum lance registrado.</p>
          )}

          <ul>
            {historico.map((lance) => (
              <li key={lance.id}>
                <strong>{lance.participante}</strong>
                {" — "}
                {dinheiro(lance.valor)}
                {" — "}
                {new Date(lance.criado_em).toLocaleString("pt-BR")}
              </li>
            ))}
          </ul>
        </div>
      </main>
    );
  }


  // Listagem dos leilões
  return (
    <main>
      <h1>Leilão em Tempo Real</h1>
      <h2>Leilões disponíveis</h2>


      <button
        onClick={() => setMostrarCadastro(!mostrarCadastro)}
      >
        {mostrarCadastro ? "Cancelar" : "+ Cadastrar leilão"}
      </button>

      {mostrarCadastro && (
        <div className="cadastro-leilao">
          <h3>Novo leilão</h3>

          <form onSubmit={cadastrarItem}>
            <label>Nome do item</label>
            <input
              type="text"
              placeholder="Ex.: Notebook"
              value={novoItem.nome}
              onChange={(e) =>
                setNovoItem({ ...novoItem, nome: e.target.value })
              }
              required
            />

            <label>Lance mínimo (R$)</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="100.00"
              value={novoItem.lance_minimo}
              onChange={(e) =>
                setNovoItem({ ...novoItem, lance_minimo: e.target.value })
              }
              required
            />

            <label>Data e horário de encerramento</label>
            <input
              type="datetime-local"
              value={novoItem.encerra_em}
              onChange={(e) =>
                setNovoItem({ ...novoItem, encerra_em: e.target.value })
              }
              required
            />

            {erroCadastro && (
              <p className="erro-lance">{erroCadastro}</p>
            )}

            <button type="submit" disabled={salvandoCadastro}>
              {salvandoCadastro ? "Salvando..." : "Cadastrar item"}
            </button>
          </form>
        </div>
      )}


      {carregando && <p>Carregando leilões...</p>}
      {erro && <p>{erro}</p>}

      {!carregando && !erro && itens.length === 0 && (
        <p>Nenhum leilão cadastrado.</p>
      )}

      <section className="lista-leiloes">
        {itens.map((item) => (
          <div className="card-leilao" key={item.id}>
            <h3>{item.nome}</h3>

            <p>
              Lance mínimo: {dinheiro(item.lance_minimo)}
            </p>

            <p>
              Lance atual:{" "}
              {item.lance_atual === null
                ? "Nenhum lance"
                : dinheiro(item.lance_atual)}
            </p>

            <p>
              Encerramento:{" "}
              {new Date(item.encerra_em).toLocaleString("pt-BR")}
            </p>

            <button onClick={() => setItemSelecionado(item)}>
              Entrar no leilão
            </button>
          </div>
        ))}
      </section>
    </main>
  );
}

export default App;
