import React from 'react';
import { observer } from 'mobx-react-lite';
import { HlsPlayer } from './components/HlsPlayer';
import streamStore from './store';

const Info = observer(({ camId }: { camId: number }) => {
  return (
    <>
      <span style={{ marginLeft: '24px' }}>{`Вероятность насилия: ${
        streamStore.getContains(camId)?.prediction ?? 'none'
      }%`}</span>
      <span style={{ marginLeft: '24px' }}>{`Задержка: ${
        streamStore.getContains(camId)?.processDelay ?? 'none'
      }`}</span>
    </>
  );
});

function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <HlsPlayer source="http://localhost:8000/streams/hls1/cam1.m3u8" />
        <Info camId={1} />
      </div>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <HlsPlayer source="http://localhost:8000/streams/hls4/cam4.m3u8" />
        <Info camId={4} />
      </div>
    </div>
  );
}

export default App;
