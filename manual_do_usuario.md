# Manual do Usuário: SJP Operacional

Este guia rápido apresenta as principais funcionalidades do **SJP Operacional (SJP Police System)**, orientando no uso das ferramentas de controle de frotas, abertura de turnos, registro de ocorrências e compartilhamento de relatórios.

---

## 🗺️ Visão Geral do Sistema
O SJP Operacional é estruturado em três módulos principais acessíveis pela barra de navegação superior:
1. **Ocorrências**: Registro de dados do serviço e geração de relatórios formatados.
2. **Frota**: Controle de viaturas, manutenções periódicas e troca de óleo.
3. **Equipamentos**: Controle dos materiais e ferramentas da unidade.
4. **Usuários** *(Visível apenas para Administradores)*: Gestão de perfis e permissões.

---

## 1. 🚗 Cadastro de Frotas e Abertura de Turno

O gerenciamento da frota é fundamental para manter a quilometragem atualizada e garantir a segurança das viaturas através do controle de manutenções.

### A. Cadastrando ou Editando uma Viatura
1. No menu superior, clique em **Frota**.
2. Para adicionar um novo veículo, clique em **Cadastrar Nova Viatura** (botão azul no canto superior direito).
3. Para editar uma viatura existente, clique no botão com ícone de lápis 📝 no cartão correspondente.
4. Preencha os campos obrigatórios:
   * **Prefixo**: Ex: *R-0123* (identificador principal da viatura)
   * **Placa**: Placa do veículo.
   * **Marca e Modelo**: Ex: *Renault Duster*.
   * **Tipo de Veículo**: Selecione entre *Carro, Moto, Furgão ou Outros*.
   * **KM Atual**: Quilometragem do veículo no momento do cadastro.
   * **Limite Troca Óleo**: Quilometragem máxima prevista para a próxima revisão/troca.
5. Clique em **Salvar**.

### B. Manutenção de Viaturas (Baixa e Retorno)
Se uma viatura apresentar problemas ou precisar ir para a oficina:
* **Baixar para Manutenção**: No cartão da viatura, clique em **Manutenção** (botão amarelo). Preencha o motivo, o local (ex: Oficina Central) e observações relevantes. A viatura mudará o status para *Baixada (Oficina)* e não poderá ser utilizada para abertura de turno.
* **Retorno à Operação**: Quando o veículo estiver pronto, clique em **Retornar à Operação** (botão verde) no respectivo cartão. O status voltará para *Operante*.
* **Histórico**: O botão **Histórico** (azul claro) exibe todos os registros passados de manutenções daquele veículo.

### C. Abertura de Turno (Início do Serviço)
A abertura do turno vincula quais viaturas estão ativas em uma data específica e registra o KM inicial de cada uma.
1. No painel de **Frota**, clique no botão **Abrir Turno** (ou vá diretamente pela URL `/frota/abertura-turno/`).
2. Selecione a **Data do Turno** no calendário.
3. O sistema carregará a lista de viaturas operantes.
4. Marque a caixa de seleção **Ativar** para as viaturas que irão rodar no dia.
5. Insira o **KM Inicial** correspondente ao início do serviço de cada viatura ativa.
6. Clique em **Salvar Abertura de Turno** no topo da página.

> [!IMPORTANT]
> A abertura do turno é um pré-requisito essencial. Sem ela, a viatura não estará disponível para seleção no módulo de registro de ocorrências na data do serviço.

---

## 2. 📝 Cadastro de Ocorrências (Registro de Turno)

Este módulo consolida toda a atividade operacional da equipe durante o serviço e gera o relatório para compartilhamento.

### Passo 1: Dados do Turno (Cabeçalho)
1. Acesse o menu **Ocorrências** (página inicial do sistema).
2. Preencha a **Data** do serviço.
3. No campo **Viatura**, selecione a viatura utilizada.
   * *Nota: O sistema carregará automaticamente o **KM Inicial** registrado na abertura do turno daquela data.*
4. Insira o **Comandante / Equipe** (ex: *SGT Silva / SD Santos*).
5. Insira o **KM Final** registrado ao término do serviço.

### Passo 2: Estatísticas e Abordagens
Utilize os painéis expansíveis (Accordions) para lançar as atividades realizadas:

* **Veículos Abordados**:
  * Insira o número de **Automóveis** e **Motocicletas** abordados.
  * Para outros tipos de veículos (ex: Ônibus, Caminhão, Bicicleta motorizada), utilize a seção inferior: selecione o tipo, digite a quantidade e clique em **Add**.
  * *Aviso: O sistema calculará de forma automática a soma de todos os veículos abordados e preencherá a quantidade inicial no campo **Condutores** na seção de Pessoas Abordadas.*

* **Pessoas Abordadas**:
  * Verifique a quantidade de **Condutores** (preenchida automaticamente baseada nos veículos abordados).
  * Preencha a quantidade de **Passageiros** e **Transeuntes** (pedestres) abordados.

* **Teste Etilométrico**:
  * Insira o número de **Testes Realizados** (bafômetro) e a quantidade de **Recusas** constatadas.

* **Apreensões e Prisões**:
  * **Prisões Efetuadas**: Selecione o sexo, digite a idade do indivíduo e clique em **Add**.
  * **Drogas Apreendidas**: Selecione o tipo da substância (Maconha, Cocaína, Crack, etc.), insira a quantidade aproximada, escolha a unidade de medida (`g`, `kg` ou `und`) e clique em **Add**.
  * **Dinheiro Apreendido**: Caso haja apreensão de dinheiro em espécie, digite o valor total em reais (R$).

* **Observações do Turno**:
  * Use este campo de texto livre para narrar os detalhes das ocorrências atendidas, números de boletins de ocorrência (B.O.), apoio a outros órgãos, ou qualquer informação relevante.

---

## 3. 🔍 Consulta de Históricos e Envio de Relatórios

O sistema permite consultar registros passados e exportar o relatório padronizado diretamente para os grupos de comunicação operacional (ex: WhatsApp).

### A. Pré-visualização e Exportação Direta (Página de Registro)
Após preencher todos os dados da ocorrência no formulário:
1. Clique no botão azul **Gerar Relatório** no final do formulário.
2. Uma prévia em formato de texto aparecerá na caixa à direita (**Resumo do Relatório**), contendo a formatação padrão da corporação (negritos em padrão markdown/whatsapp, marcadores de lista, etc.).
3. Clique em:
   * **Salvar no Banco** (botão azul claro) para registrar os dados no sistema.
   * **Enviar p/ WhatsApp** (botão verde) para abrir o WhatsApp Web/Desktop com o texto do relatório pré-preenchido e pronto para ser enviado ao grupo da equipe.

### B. Consulta ao Histórico
Para consultar registros anteriores salvos no banco de dados:
1. Clique no botão **Histórico** (no menu superior ou no topo do formulário de ocorrências).
2. Você verá uma lista ordenada por data contendo: *Data, Viatura, Comandante e Data/Hora de Salvamento*.
3. **Filtro**: Use o campo **Filtrar por Data** no topo e clique em **Buscar** para localizar um dia específico de serviço.

### C. Ações no Histórico
Para cada registro listado no histórico, estão disponíveis as seguintes ações:
1. **Enviar via WhatsApp (Ícone do WhatsApp 🟢)**: Gera instantaneamente o texto formatado daquele turno e abre a interface de envio do WhatsApp, sem precisar entrar na edição.
2. **Editar Ocorrência (Ícone de Lápis 📝)**: Carrega todas as informações daquele turno de volta no formulário da página inicial, permitindo correções ou inclusão de novos dados operacionais. Ao finalizar, basta clicar em **Atualizar no Banco**.
3. **Excluir (Ícone de Lixeira 🔴)**:
   > [!WARNING]
   > A exclusão é permanente e está disponível apenas para usuários com perfil de **Administrador** ou **Admin Master**. O sistema solicitará uma confirmação antes de apagar o registro.

---

## 📊 Estatísticas Operacionais
No botão **Estatísticas** (dentro do módulo de ocorrências), é possível visualizar gráficos consolidados de produtividade do período selecionado, tais como o total de pessoas e veículos abordados, testes etilométricos e o balanço de apreensões efetuadas pela unidade operacional.
