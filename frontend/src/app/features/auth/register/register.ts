import { Component, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Store } from '@ngrx/store';
import { RouterLink } from '@angular/router';
import * as AuthActions from '../store/auth.actions';
import {
  selectAuthLoading,
  selectAuthError,
  selectRegistrationComplete,
} from '../store/auth.selectors';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { InputComponent } from '../../../shared/ui/input/input';
import { ButtonComponent } from '../../../shared/ui/button/button';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, InputComponent, ButtonComponent],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
  private readonly store = inject(Store);
  private readonly fb = inject(FormBuilder);

  readonly loading = this.store.selectSignal(selectAuthLoading);
  readonly error = this.store.selectSignal(selectAuthError);
  readonly registrationComplete = this.store.selectSignal(selectRegistrationComplete);

  form = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { firstName, lastName, email, password } = this.form.getRawValue();
    this.store.dispatch(
      AuthActions.register({
        first_name: firstName!,
        last_name: lastName!,
        email: email!,
        password: password!,
      }),
    );
  }

  resendVerification(): void {
    const email = this.form.getRawValue().email;
    if (email) {
      this.store.dispatch(AuthActions.resendVerification({ email }));
    }
  }
}
