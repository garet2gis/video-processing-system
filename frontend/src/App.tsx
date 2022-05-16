import React from 'react';
import { observer } from 'mobx-react-lite';

import { Layout } from 'antd';

import { HlsPlayer } from './components/HlsPlayer';
import streamStore from './store';
import './App.css';

const Info = observer(({ camId }: { camId: number }) => {
  const prob = streamStore.getContains(camId)?.prediction;

  let color = 'rgba(255, 255, 255, 0.85)';

  if (prob !== undefined) {
    color = prob > 80 ? 'red' : prob > 50 ? 'orange' : 'rgba(255, 255, 255, 0.85)';
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '150px',
        height: '42px',
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: 67,
        zIndex: 1,
        fontSize: '12px',
        textShadow: '1px 1px 2px black',
        fontWeight: 'bold',
        backgroundColor: 'black',
      }}>
      <span
        style={{
          marginLeft: '24px',
          color: color,
        }}>{`Насилие: ${prob ?? 'none'}%`}</span>
      <span style={{ marginLeft: '24px' }}>{`Задержка: ${
        streamStore.getContains(camId)?.processDelay ?? 'none'
      }`}</span>
    </div>
  );
});

const Row: React.FC = ({ children }) => {
  return <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>{children}</div>;
};

const Element: React.FC<{ needMargin?: boolean }> = ({ children, needMargin }) => {
  const margin = needMargin !== undefined ? { marginRight: '8px' } : {};
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        position: 'relative',
        width: '40%',
        minWidth: '500px',
        ...margin,
      }}>
      {children}
    </div>
  );
};

function App() {
  return (
    <Layout className="layout" style={{ display: 'flex', height: '100vh' }}>
      <Layout.Header>
        <div className="logo" />
        <h1>Cистема обработки видео: демо</h1>
      </Layout.Header>
      <Layout.Content>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            margin: '8px',
          }}>
          <Row>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls1/cam1.m3u8" />
              <Info camId={1} />
            </Element>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls1/cam1.m3u8" />
              <Info camId={1} />
            </Element>
          </Row>

          <Row>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls2/cam2.m3u8" />
              <Info camId={2} />
            </Element>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls2/cam2.m3u8" />
              <Info camId={2} />
            </Element>
          </Row>

          <Row>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls2/cam2.m3u8" />
              <Info camId={2} />
            </Element>
            <Element needMargin>
              <HlsPlayer source="http://localhost:8000/streams/hls2/cam2.m3u8" />
              <Info camId={2} />
            </Element>
          </Row>
        </div>
      </Layout.Content>
      <Layout.Footer className={'footer'} style={{ textAlign: 'right', color: 'gray', alignSelf: 'flex-end' }}>
        Сделано Муковским Даниилом, группа 8383
      </Layout.Footer>
    </Layout>
  );
}

export default App;
