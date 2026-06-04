import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-metrics',
  standalone: true,
  template: `
    <div class="metrics-container">
      <iframe [src]="metricsUrl" class="metrics-frame" title="Metrics Dashboard"></iframe>
    </div>
  `,
  styles: [
    `
      .metrics-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
        overflow: hidden;
      }

      .metrics-frame {
        flex: 1;
        width: 100%;
        height: 100%;
        border: none;
        min-height: calc(100vh - 64px);
      }
    `,
  ],
})
export class MetricsComponent {
  readonly metricsUrl: SafeResourceUrl;

  constructor(sanitizer: DomSanitizer) {
    this.metricsUrl = sanitizer.bypassSecurityTrustResourceUrl('http://localhost:8501/');
  }
}
