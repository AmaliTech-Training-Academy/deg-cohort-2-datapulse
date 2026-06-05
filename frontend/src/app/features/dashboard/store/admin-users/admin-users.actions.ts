import { createAction, props } from '@ngrx/store';
import { AdminUser } from '../../models/admin-user.model';

export const loadAdminUsers = createAction('[Admin Users] Load');
export const loadAdminUsersSuccess = createAction(
  '[Admin Users] Load Success',
  props<{ users: AdminUser[]; total: number }>(),
);
export const loadAdminUsersFailure = createAction(
  '[Admin Users] Load Failure',
  props<{ error: string }>(),
);
export const clearAdminUsers = createAction('[Admin Users] Clear');
