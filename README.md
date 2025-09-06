# Dashboard GLPI - Análise de Tickets

Dashboard interativo criado com Streamlit para análise de dados de tickets do sistema GLPI.

## Funcionalidades

- **📊 Métricas Gerais**: Total de tickets, pendentes, em atendimento e solucionados
- **📈 Gráficos Interativos**: 
  - Distribuição por status (pizza)
  - Tickets por prioridade (barras)
  - Timeline de criação de tickets
  - Top departamentos e localizações
  - Performance por técnico
- **🔍 Filtros**: Status, prioridade e departamento
- **📤 Upload de Dados**: Atualização automática via upload de CSV
- **📋 Tabela Detalhada**: Visualização completa dos dados filtrados

## Como Executar

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o dashboard:
```bash
streamlit run dashboard.py
```

3. Acesse no navegador: `http://localhost:8501`

## Estrutura dos Dados

O dashboard espera um arquivo CSV com separador `;` contendo as seguintes colunas:
- ID, Título, Entidade, Localização
- Status, Data de abertura, Última atualização
- Requerente, Técnico atribuído
- Categoria, Prioridade, Departamento

## Atualização de Dados

- **Automática**: Coloque o novo arquivo `glpi.csv` no diretório
- **Manual**: Use o upload na barra lateral do dashboard