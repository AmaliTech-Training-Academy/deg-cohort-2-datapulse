import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Store } from '@ngrx/store';
import { RouterLink } from '@angular/router';
import * as AuthActions from '../store/auth.actions';
import {
  selectAuthError,
  selectAuthLoading,
  selectEmailVerificationSent,
  selectEmailVerified,
} from '../store/auth.selectors';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { ButtonComponent } from '../../../shared/ui/button/button';
import { InputComponent } from '../../../shared/ui/input/input';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, ButtonComponent, InputComponent],
  templateUrl: './verify-email.html',
  styleUrl: './verify-email.css',
})
export class VerifyEmailComponent implements OnInit {
  private readonly store = inject(Store);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  readonly loading = this.store.selectSignal(selectAuthLoading);
  readonly error = this.store.selectSignal(selectAuthError);
  readonly verified = this.store.selectSignal(selectEmailVerified);
  readonly resendSent = this.store.selectSignal(selectEmailVerificationSent);

  resendForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
  });

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');
    if (token) {
      this.store.dispatch(AuthActions.verifyEmail({ token }));
    }
  }

  resend(): void {
    if (this.resendForm.invalid) {
      this.resendForm.markAllAsTouched();
      return;
    }
    const { email } = this.resendForm.getRawValue();
    this.store.dispatch(AuthActions.resendVerification({ email: email! }));
  }
}
