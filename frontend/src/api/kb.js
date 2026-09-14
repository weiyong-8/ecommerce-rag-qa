import request from './request'

export const uploadDocument = (formData) =>
  request.post('/kb/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
export const listDocuments = () => request.get('/kb/documents')
export const deleteDocument = (id) => request.delete(`/kb/documents/${id}`)
export const reprocessDocument = (id) => request.post(`/kb/documents/${id}/reprocess`)
export const kbStats = () => request.get('/kb/stats')
