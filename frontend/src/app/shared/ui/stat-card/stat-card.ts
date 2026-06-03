import { Component, input } from '@angular/core';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [NgClass],
  templateUrl: './stat-card.html',
  styleUrl: './stat-card.css',
})
export class StatCardComponent {
  readonly label = input<string>('');
  readonly value = input<string | number>('');
  readonly subtitle = input<string>('');
  readonly valueClass = input<string>('');
}
