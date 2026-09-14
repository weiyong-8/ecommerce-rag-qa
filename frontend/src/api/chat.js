import request from './request'

export const listConversations = () => request.get('/conversations')
export const createConversation = (data) => request.post('/conversations', data)
export const renameConversation = (id, data) => request.patch(`/conversations/${id}`, data)
export const deleteConversation = (id) => request.delete(`/conversations/${id}`)
export const listMessages = (id) => request.get(`/conversations/${id}/messages`)

// SSE 流式问答(fetch 流式读取,POST 无法用 EventSource)
// handlers: onToken / onSources / onDone / onError
export async function streamAsk(conversationId, question, handlers) {
  const res = await fetch(`/api/conversations/${conversationId}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify({ question }),
  })
  if (!res.ok || !res.body) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `HTTP ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const raw = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      for (const line of raw.split('\n')) {
        if (!line.startsWith('data: ')) continue
        let data
        try {
          data = JSON.parse(line.slice(6))
        } catch {
          continue
        }
        if (data.type === 'token') handlers.onToken?.(data.content)
        else if (data.type === 'sources') handlers.onSources?.(data.sources)
        else if (data.type === 'done') handlers.onDone?.()
        else if (data.type === 'error') handlers.onError?.(data.message)
      }
    }
  }
}
