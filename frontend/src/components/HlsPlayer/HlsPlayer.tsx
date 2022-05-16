import { useEffect, useRef } from 'react';
import ReactHlsPlayer from 'react-hls-player';

interface Props {
  source: string;
}

function HlsPlayer({ source }: Props): JSX.Element {
  const playerRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    playerRef.current?.play();
  }, []);

  return (
    <ReactHlsPlayer
      playerRef={playerRef}
      src={source}
      autoPlay={true}
      controls={true}
      width={'auto'}
      height="200px"
      hlsConfig={{
        enableWorker: true,
        maxLoadingDelay: 4,
        minAutoBitrate: 0,
        lowLatencyMode: true,
        autoStartLoad: true,
        debug: false,
        liveDurationInfinity: true,
      }}
    />
  );
}

export default HlsPlayer;
