# Security

This project calls paid TTS APIs. Treat API keys as secrets.

## Do Not Commit

The repository ignores common secret and local-data files:

- `*.key`
- `.env`
- `.env.*`
- `config.yaml`
- `input/`
- `output/`

Keep real keys in ignored files such as:

```text
aliyun.key
mimo.key
```

or pass them through environment variables:

```bash
export DASHSCOPE_API_KEY="sk-..."
export MIMO_API_KEY="sk-or-tp-..."
```

## Before Publishing

Run these checks before pushing to a public repository:

```bash
git status --short
git ls-files | rg '(\.key$|\.env$|input/|output/)'
rg -n 'sk-|tp-|DASHSCOPE_API_KEY=|MIMO_API_KEY=' .
```

The second command should print nothing for local keys and generated data. The third command may find documentation placeholders; it should not find real keys.

## API Key Rotation

If a key is ever committed or shared by mistake, revoke it immediately in the provider console and create a new one.

Provider docs:

- Alibaba Cloud Model Studio API keys: <https://help.aliyun.com/zh/model-studio/get-api-key>
- Xiaomi MiMo tools overview: <https://platform.xiaomimimo.com/docs/zh-CN/integration/tools-overview>
