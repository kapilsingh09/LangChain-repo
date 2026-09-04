import { useState, useCallback, useRef } from 'react';
import { API_BASE_URL } from '../api/client';

const INITIAL_STATE = {
  thread_id: null,
  question: '',
  status: 'idle', // idle, researching, completed, error
  nodes: {
    planner: { status: 'pending' }, // pending, active, completed
    researcher: { status: 'pending' },
    collector: { status: 'pending' },
    critic: { status: 'pending' },
    report_writer: { status: 'pending' },
    image_subgraph: { status: 'pending' },
    file_saver: { status: 'pending' },
  },
  events: [],
  tasks: [],
  evidence: [],
  final_report: '',
  error: null,
};

// Node execution order for visual representation
const NODE_ORDER = [
  'planner',
  'researcher',
  'collector',
  'critic',
  'report_writer',
  'image_subgraph',
  'file_saver'
];

export function useResearchStream() {
  const [state, setState] = useState(INITIAL_STATE);
  const abortControllerRef = useRef(null);

  const processNodeUpdate = (node, data, prevState) => {
    const newState = { ...prevState };
    newState.nodes = { ...prevState.nodes };

    // Mark previous nodes as completed, current as active
    let reachedCurrent = false;
    for (const n of NODE_ORDER) {
      if (n === node) {
        newState.nodes[n] = { status: 'active' };
        reachedCurrent = true;
      } else if (!reachedCurrent) {
        newState.nodes[n] = { status: 'completed' };
      }
    }

    // Extract specific data based on node
    if (node === 'planner' && data.research_tropics_planned) {
      newState.tasks = data.research_tropics_planned;
    }
    
    // Combine research results if we are at collector or after
    if (data.collected_researchs) {
       newState.evidence = data.collected_researchs;
    } else if (data.research_results && Array.isArray(data.research_results)) {
       // Just as a fallback if collected_researchs isn't there
       newState.evidence = data.research_results.map(r => ({ finding: r, source: 'Researcher' }));
    }

    if (data.final_report) {
      newState.final_report = data.final_report;
    }

    return newState;
  };

  const startResearch = useCallback(async (question, threadId = null) => {
    // Reset state
    setState({ ...INITIAL_STATE, question, status: 'researching' });

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}/api/research/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ question, thread_id: threadId }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE format
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep the incomplete part in the buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;

            try {
              const payload = JSON.parse(dataStr);
              
              setState(prevState => {
                const newEvents = [...prevState.events, { id: Date.now() + Math.random(), ...payload, timestamp: new Date().toISOString() }];
                let nextState = { ...prevState, events: newEvents };

                if (payload.event === 'started') {
                  nextState.thread_id = payload.thread_id;
                  nextState.status = 'researching';
                } 
                else if (payload.event === 'node_update') {
                  nextState = processNodeUpdate(payload.node, payload.data, nextState);
                } 
                else if (payload.event === 'completed') {
                  nextState.status = 'completed';
                  // Mark all nodes completed
                  for (const n of NODE_ORDER) {
                    nextState.nodes[n] = { status: 'completed' };
                  }
                  if (payload.data?.final_report) {
                    nextState.final_report = payload.data.final_report;
                  }
                } 
                else if (payload.event === 'error') {
                  nextState.status = 'error';
                  nextState.error = payload.error;
                }

                return nextState;
              });
            } catch (err) {
              console.error('Failed to parse SSE JSON:', err, dataStr);
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted');
      } else {
        console.error('Stream error:', err);
        setState(prev => ({ ...prev, status: 'error', error: err.message }));
      }
    }
  }, []);

  const cancelResearch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setState(prev => ({ ...prev, status: 'error', error: 'Research cancelled by user.' }));
    }
  }, []);

  const clearResearch = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    state,
    startResearch,
    cancelResearch,
    clearResearch
  };
}
