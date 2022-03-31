import React from 'react';
import { HlsPlayer } from './components/HlsPlayer';

function App() {
  return (
    <>
      <HlsPlayer source="http://localhost:8000/streams/hls1/cam1.m3u8" />
      <HlsPlayer source="http://localhost:8000/streams/hls2/cam2.m3u8" />
    </>
  );
}

export default App;
