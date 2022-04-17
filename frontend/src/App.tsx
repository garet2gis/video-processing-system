import React, { useEffect } from 'react';
import { HlsPlayer } from './components/HlsPlayer';

function App() {
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8010/');

    ws.onmessage = (event: MessageEvent) => {
      const errors = JSON.parse(event.data)?.errors;
      if (errors) console.log('ws errors');
      else console.log(event.data);
    };
  }, []);

  return (
    <>
      <HlsPlayer source="http://localhost:8000/streams/hls1/cam1.m3u8" />
      <HlsPlayer source="http://localhost:8000/streams/hls4/cam4.m3u8" />
    </>
  );
}

export default App;
