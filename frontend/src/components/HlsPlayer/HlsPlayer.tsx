import { useRef } from 'react';
import ReactHlsPlayer from 'react-hls-player';

interface Props {
  source: string;
}

function HlsPlayer({ source }: Props): JSX.Element {
  const playerRef = useRef<HTMLVideoElement>(null);

  return (
    <ReactHlsPlayer
      playerRef={playerRef}
      src={source}
      autoPlay={false}
      controls={true}
      width="60%"
      height="auto"
      hlsConfig={{
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
