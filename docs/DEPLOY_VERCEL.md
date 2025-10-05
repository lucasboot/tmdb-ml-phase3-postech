# Guia de Deploy na Vercel

Este guia descreve como publicar o projeto **tmdb-ml-phase3-postech** na
[Vercel](https://vercel.com) utilizando as configurações já presentes no
repositório (`vercel.json` e `api/index.py`). O processo garante que a
aplicação Flask rode como uma Function e que a versão exibida na interface
seja atualizada automaticamente a cada commit enviado para a branch
`main`.

## 1. Pré-requisitos

1. Conta ativa na Vercel (plano gratuito é suficiente).
2. Repositório hospedado no GitHub, GitLab ou Bitbucket com acesso pela
   Vercel.
3. Banco de dados Postgres acessível pela internet e um serviço Redis
   (podem ser SaaS externos como Railway, Render, Supabase, Upstash etc.).
4. As variáveis de ambiente necessárias (veja a lista abaixo).

## 2. Estrutura preparada neste repositório

- `vercel.json`: define que tudo é servido pela Function Python em
  `api/index.py`.
- `api/index.py`: ponto de entrada que instancia o Flask app (via
  `web.app.create_app`).
- A aplicação injeta automaticamente a versão (`APP_VERSION` ou
  `VERCEL_GIT_COMMIT_SHA`) na interface e no endpoint `/health`.

Nenhuma configuração extra precisa ser feita no painel para apontar para
subdiretórios: o deploy a partir da raiz já funciona.

## 3. Variáveis de ambiente obrigatórias

Configure as variáveis em **Project Settings → Environment Variables** na
Vercel. Defina os valores para os escopos **Production** e **Preview** (ou
utilize `vercel env add` pela CLI):

| Variável | Descrição |
| --- | --- |
| `SECRET_KEY` | Chave secreta Flask para cookies/sessões. Utilize um valor aleatório. |
| `DATABASE_URL` | URL completa de conexão com Postgres (`postgresql+psycopg2://...`). |
| `TMDB_API_KEY` | Chave da API do TMDB utilizada pelos jobs e endpoints. |
| `REDIS_URL` | URL do Redis utilizado pelos workers/queues. Ex.: `rediss://...` |
| `POLL_INTERVAL_MS` | (Opcional) Intervalo de atualização do dashboard em milissegundos. |
| `APP_VERSION` | (Opcional) Caso deseje sobrescrever a versão exibida. Quando não definido, a Vercel usará automaticamente o `VERCEL_GIT_COMMIT_SHA` da build. |

> 💡 As variáveis podem ser copiadas do arquivo `env.sample` para facilitar a
> checagem dos nomes.

## 4. Conectando o repositório na Vercel

1. Acesse o dashboard da Vercel e clique em **Add New… → Project**.
2. Selecione a opção **Import Git Repository** e escolha este repositório.
3. No passo "Configure Project":
   - **Framework Preset**: escolha **Other** (o `vercel.json` já cobre o
     build).
   - **Root Directory**: mantenha `./` (raiz do projeto).
   - Confirme as variáveis de ambiente ou deixe para configurar após a
     importação.
4. Clique em **Deploy** para que a primeira build seja executada.

## 5. Banco de dados e migrações

A Vercel não executa scripts extras automaticamente. Após provisionar o
Postgres e o Redis:

1. Exporte as variáveis `DATABASE_URL` e `REDIS_URL` localmente (ex.: via
   `.env`).
2. Rode as migrações com o Python local (ou em uma máquina com acesso ao
   banco):

   ```bash
   pip install -r requirements.txt
   export DATABASE_URL="postgresql+psycopg2://..."
   python -m web.app.migrate_db
   ```

   Repita o procedimento sempre que o schema mudar.

## 6. Atualização automática da versão

- A aplicação lê `APP_VERSION`. Se não estiver definida, usa a variável
  `VERCEL_GIT_COMMIT_SHA` fornecida pela Vercel.
- Cada novo commit na branch `main` gera uma build. Para garantir isso:
  1. Nas configurações do projeto, em **Git → Production Branch**, mantenha
     `main`.
  2. Habilite **Deploy Hooks** somente se precisar acionar builds de fora
     do Git.
- O footer do dashboard e o endpoint `/health` passam a exibir a versão
  curta (7 caracteres) correspondente ao commit da build.

## 7. Deploy manual opcional com a CLI

Se preferir disparar deploys localmente:

```bash
npm i -g vercel
vercel login
vercel link  # selecione o projeto
vercel env pull .env.vercel
vercel --prod
```

Garanta que o arquivo `.env.vercel` contenha as variáveis descritas acima.

## 8. Pós-deploy e verificação

1. Após cada build, verifique `https://<seu-projeto>.vercel.app/health`.
   Ele deve retornar `{ "status": "ok", "version": "<hash>" }`.
2. Confirme no dashboard se a versão exibida no rodapé corresponde ao
   commit mais recente.
3. Use os logs do deploy na Vercel para depurar eventuais erros de
   conexão com banco/Redis.

Pronto! Com essas configurações, qualquer commit na branch `main` aciona um
novo deploy na Vercel e atualiza automaticamente a versão mostrada pela
aplicação.
