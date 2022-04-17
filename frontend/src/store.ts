import { makeAutoObservable } from 'mobx';

/**
 * Глобальный стор общего назначения
 */
class StreamStore {
  constructor() {
    makeAutoObservable(this, undefined, { autoBind: true });

    this.ws = new WebSocket('ws://localhost:8010/');

    this.ws.onmessage = (event: MessageEvent) => {
      const errors = JSON.parse(event.data)?.errors;
      if (errors) console.log('ws errors');
      else {
        const message: { cam_id: string; is_violence: string } = JSON.parse(event.data);

        const data: { camId: number; prediction: number } = {
          camId: Number(message.cam_id),
          prediction: Number((Number(message.is_violence) * 100).toFixed(2)),
        };

        const cam = this.getContains(data.camId);

        if (cam === undefined) {
          this.camerasPrediction.push(data);
        } else {
          cam.prediction = data.prediction;
        }
      }
    };
  }

  private ws: WebSocket;

  public camerasPrediction: { camId: number; prediction: number }[] = [];

  public getContains(camId: number) {
    return this.camerasPrediction.find((e) => e.camId === camId);
  }
}

export default new StreamStore();
