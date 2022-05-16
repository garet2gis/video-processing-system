import { makeAutoObservable } from 'mobx';

/**
 * Глобальный стор общего назначения
 */
interface CameraPrediction {
  camId: number;
  prediction: number;
  processDelay: string;
}

class StreamStore {
  constructor() {
    makeAutoObservable(this, undefined, { autoBind: true });

    this.ws = new WebSocket('ws://localhost:8006/predictions');

    this.ws.onmessage = (event: MessageEvent) => {
      const errors = JSON.parse(event.data)?.errors;
      if (errors) console.log('ws errors');
      else {
        const message: { cam_id: string; prediction: string; timestamp: number; timestamp_delay: number } = JSON.parse(
          event.data
        );

        const delay = (new Date().getTime() - message.timestamp_delay * 1000) / 1000;

        const data: CameraPrediction = {
          camId: Number(message.cam_id),
          prediction: Number((Number(message.prediction) * 100).toFixed(2)),
          processDelay: delay.toFixed(2),
        };

        const cam = this.getContains(data.camId);

        if (cam === undefined) {
          this.camerasPrediction.push(data);
        } else {
          cam.prediction = data.prediction;
          cam.processDelay = data.processDelay;
        }
      }
    };
  }

  private ws: WebSocket;

  public camerasPrediction: CameraPrediction[] = [];

  public getContains(camId: number) {
    return this.camerasPrediction.find((e) => e.camId === camId);
  }
}

export default new StreamStore();
