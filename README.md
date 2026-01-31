# Sistema de Controle de Estoque – Vila Vicentina Abaeté

Aplicação desktop desenvolvida em Python para controle de estoque de doações da **Vila Vicentina de Abaeté**.

O projeto nasceu de uma necessidade real: organizar a entrada e saída de alimentos e itens doados, evitar perdas por falta de controle e facilitar o acompanhamento de estoque mínimo no dia a dia da instituição.

---

## 🎯 Objetivo do projeto

Criar uma aplicação simples, funcional e estável para uso real, sem depender de conhecimento técnico por parte do usuário final.

O foco não foi “mostrar tecnologia”, mas **resolver um problema prático**, com uma interface direta e dados persistentes.

---

## 🧩 Funcionalidades

- Cadastro de produtos com unidade e estoque mínimo  
- Entrada e saída de estoque  
- Listagem e busca de produtos (com filtro progressivo)  
- Identificação automática de itens abaixo do estoque mínimo  
- Persistência local dos dados (sem risco de perda ao fechar o app)  
- API interna para integração e futuras expansões  

---

## 🖥️ Interface (GUI)

- Interface gráfica desenvolvida com **Tkinter**
- Busca inteligente com:
  - rolagem
  - filtro por início do nome (startswith)
  - filtro por conteúdo (contains)
- Pensada para uso por pessoas sem familiaridade com sistemas complexos

---

## 🔗 API

O projeto possui uma **API REST interna** desenvolvida com **FastAPI**, utilizada como camada de serviço:

- Centraliza regras de negócio
- Garante consistência entre interface e dados
- Facilita futuras integrações (ex: relatórios, rede local, web)

---

## 🧠 Arquitetura e decisões técnicas

- Separação clara de responsabilidades:
  - `gui.py` → interface
  - `estoque_core.py` → regras de negócio e persistência
  - `api.py` → camada de serviço
- O **core é a única fonte de verdade** para os dados
- Persistência em `%APPDATA%` (padrão de aplicações desktop no Windows)
- Backups automáticos dos dados
- Estrutura organizada para evitar acoplamento e retrabalho

---

## 📦 Distribuição

A aplicação é empacotada como **executável (.exe)** usando PyInstaller.

- Não requer Python instalado
- Basta copiar a pasta e executar
- Cada usuário possui seus próprios dados locais

---

## 🚀 Motivação pessoal

Este projeto faz parte do meu processo de aprendizado prático em desenvolvimento de software.

Mais do que “funcionar”, o foco foi:
- organizar código
- lidar com refatoração real
- resolver problemas de estrutura, imports e build
- entregar algo utilizável fora do ambiente de desenvolvimento

É um projeto simples em escopo, mas **real em complexidade**.

---

## 🛠️ Tecnologias utilizadas

- Python
- Tkinter
- FastAPI
- PyInstaller
- Git / GitHub

---

## 📌 Status

Projeto funcional, em uso de testes e preparado para futuras melhorias, como:
- relatórios
- exportação de dados
- controle de usuários
- execução em rede local
