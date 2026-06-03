import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MockDataService } from '../../../../../shared/services/mock-data.service';
import { QualityThresholds } from '../../../../../shared/models/dashboard.models';
import { BadgeComponent } from '../../../../../shared/ui/badge/badge';

@Component({
  selector: 'app-quality-thresholds',
  standalone: true,
  imports: [FormsModule, BadgeComponent],
  templateUrl: './quality-thresholds.html',
  styleUrl: './quality-thresholds.css',
})
export class QualityThresholdsComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected thresholds = signal<QualityThresholds>({
    healthyMin: 85,
    warningMin: 70,
    autoPauseAfterFailures: 3,
    slowRunThresholdSeconds: 180,
  });
  protected saving = signal(false);
  protected saved = signal(false);

  protected healthyMin = 85;
  protected warningMin = 70;
  protected autoPause = 3;
  protected slowRunMins = 3;
  protected slowRunSecs = 0;

  ngOnInit(): void {
    this.dataService.getSettings().subscribe((s) => {
      this.thresholds.set(s);
      this.healthyMin = s.healthyMin;
      this.warningMin = s.warningMin;
      this.autoPause = s.autoPauseAfterFailures;
      this.slowRunMins = Math.floor(s.slowRunThresholdSeconds / 60);
      this.slowRunSecs = s.slowRunThresholdSeconds % 60;
    });
  }

  protected onSave(): void {
    this.saving.set(true);
    this.saved.set(false);
    const settings: QualityThresholds = {
      healthyMin: this.healthyMin,
      warningMin: this.warningMin,
      autoPauseAfterFailures: this.autoPause,
      slowRunThresholdSeconds: this.slowRunMins * 60 + this.slowRunSecs,
    };
    this.dataService.saveSettings(settings).subscribe(() => {
      this.saving.set(false);
      this.saved.set(true);
      setTimeout(() => this.saved.set(false), 2000);
    });
  }
}
