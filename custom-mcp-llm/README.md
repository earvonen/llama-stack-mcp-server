## Draft Finnish MCP Server

This repository provides a Model Context Protocol (MCP) server that forwards
requests to an external vLLM deployment. The MCP server exposes a single tool,
`draft_finnish`, that helps author Finnish prose by delegating to
the configured model.

## Local Development and Testing

### Setup a venv

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install fastmcp==2.2.2 httpx
```

### Configure the vLLM connection

The MCP server expects an OpenAI-compatible vLLM endpoint. Configure the
connection with environment variables:

- `VLLM_ENDPOINT` (required): the full URL to the `/v1/chat/completions` route
  exposed by vLLM.
- `VLLM_MODEL` (optional): overrides the model name sent to the endpoint. If not
  provided, the server defaults to `meta-llama/Llama-3.1-8B-Instruct`.
- `VLLM_API_KEY` (optional): bearer token that will be forwarded as the
  `Authorization` header.
- `DRAFT_FINNISH_SYSTEM_PROMPT` (optional): custom system prompt for the tool.

Example configuration:

```bash
export VLLM_ENDPOINT="http://localhost:8000/v1/chat/completions"
export VLLM_MODEL="meta-llama/Llama-3.1-8B-Instruct"
```

### Run the MCP server

The server listens on port 8000 by default.

```bash
python helsinki_transport.py
```

### Test the server

The provided smoke test prints the mocked response from the vLLM endpoint:

```bash
python test_helsinki_transport.py
```

## Available Tools

### `draft_finnish`

Parameters:

- `prompt` (required): text prompt to send to the external model.
- `temperature` (optional, default `0.7`): sampling temperature forwarded to
  vLLM.
- `max_tokens` (optional, default `1024`): maximum number of tokens to generate.
- `top_p` (optional, default `0.9`): nucleus sampling parameter.
- `system_prompt` (optional): overrides the default Finnish system prompt.

The tool returns the first completion produced by the upstream vLLM server.

## Llama Stack Integration

### Review registered tool groups

```bash
LLAMA_STACK_ENDPOINT=http://localhost:8321
curl -sS $LLAMA_STACK_ENDPOINT/v1/toolgroups -H "Content-Type: application/json" | jq
```

### Register the Draft Finnish MCP server

If running Llama Stack in a container:

```bash
curl -X POST -H "Content-Type: application/json" --data '{ "provider_id" : "model-context-protocol", "toolgroup_id" : "mcp::draft-finnish", "mcp_endpoint" : { "uri" : "http://host.docker.internal:8000/sse"}}' $LLAMA_STACK_ENDPOINT/v1/toolgroups
```

Else:

```bash
curl -X POST -H "Content-Type: application/json" --data '{ "provider_id" : "model-context-protocol", "toolgroup_id" : "mcp::draft-finnish", "mcp_endpoint" : { "uri" : "http://localhost:8000/sse"}}' $LLAMA_STACK_ENDPOINT/v1/toolgroups
```

### Check registration

```bash
curl -sS $LLAMA_STACK_ENDPOINT/v1/toolgroups -H "Content-Type: application/json" | jq
```

### Test connectivity

```bash
API_KEY=none
LLAMA_STACK_ENDPOINT=http://localhost:8321

curl -sS $LLAMA_STACK_ENDPOINT/v1/inference/chat-completion \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
     \"model_id\": \"$LLAMA_STACK_MODEL\",
     \"messages\": [{\"role\": \"user\", \"content\": \"Kirjoita lyhyt tervehdys suomeksi.\"}],
     \"temperature\": 0.0
   }" | jq -r '.completion_message | select(.role == "assistant") | .content'
```



