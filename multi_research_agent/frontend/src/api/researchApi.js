import { fetchJson, API_BASE_URL } from './client';

export const researchApi = {
  executeResearch: async (question, threadId = null) => {
    return fetchJson('/api/research', {
      method: 'POST',
      body: JSON.stringify({ question, thread_id: threadId }),
    });
  },

  getStreamUrl: () => {
    return `${API_BASE_URL}/api/research/stream`;
  }
};
