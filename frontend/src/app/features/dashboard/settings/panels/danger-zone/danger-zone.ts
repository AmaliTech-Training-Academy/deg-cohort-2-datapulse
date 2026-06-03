import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-danger-zone',
  standalone: true,
  templateUrl: './danger-zone.html',
  styleUrl: './danger-zone.css',
})
export class DangerZoneComponent {
  protected confirmDelete = signal(false);

  protected onDeleteOrg(): void {
    this.confirmDelete.set(true);
  }
}
