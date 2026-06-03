import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard, roleRedirectGuard } from './core/guards/role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register/register').then((m) => m.RegisterComponent),
  },
  {
    path: 'reset-password',
    loadComponent: () =>
      import('./features/auth/reset-password/reset-password').then((m) => m.ResetPasswordComponent),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.DashboardComponent),
    children: [
      {
        path: '',
        canActivate: [roleRedirectGuard],
        children: [],
      },
      // Admin-only routes
      {
        path: 'overview',
        canActivate: [roleGuard('admin')],
        loadComponent: () =>
          import('./features/dashboard/admin/overview/overview').then((m) => m.OverviewComponent),
      },
      {
        path: 'all-projects',
        canActivate: [roleGuard('admin')],
        loadComponent: () =>
          import('./features/dashboard/admin/all-projects/all-projects').then(
            (m) => m.AllProjectsComponent,
          ),
      },
      {
        path: 'users',
        canActivate: [roleGuard('admin')],
        loadComponent: () =>
          import('./features/dashboard/admin/users/users').then((m) => m.UsersComponent),
      },
      // User project routes
      {
        path: 'projects',
        children: [
          {
            path: '',
            loadComponent: () =>
              import('./features/dashboard/user/projects/projects').then(
                (m) => m.MyProjectsComponent,
              ),
          },
          {
            path: 'new',
            loadComponent: () =>
              import('./features/dashboard/user/new-project/new-project').then(
                (m) => m.NewProjectComponent,
              ),
          },
          {
            path: ':id',
            loadComponent: () =>
              import('./features/dashboard/user/project-detail/project-detail').then(
                (m) => m.ProjectDetailComponent,
              ),
          },
          {
            path: ':id/:datasetId',
            loadComponent: () =>
              import('./features/dashboard/user/quality-report/quality-report').then(
                (m) => m.QualityReportComponent,
              ),
          },
        ],
      },
      // Shared routes (both roles)
      {
        path: 'alerts',
        loadComponent: () =>
          import('./features/dashboard/alerts/alerts').then((m) => m.AlertsComponent),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/dashboard/settings/settings').then((m) => m.SettingsComponent),
        children: [
          { path: '', redirectTo: 'quality-thresholds', pathMatch: 'full' },
          {
            path: 'quality-thresholds',
            loadComponent: () =>
              import('./features/dashboard/settings/panels/quality-thresholds/quality-thresholds').then(
                (m) => m.QualityThresholdsComponent,
              ),
          },
          {
            path: 'general',
            loadComponent: () =>
              import('./features/dashboard/settings/panels/general/general').then(
                (m) => m.GeneralSettingsComponent,
              ),
          },
          {
            path: 'notifications',
            loadComponent: () =>
              import('./features/dashboard/settings/panels/notifications/notifications').then(
                (m) => m.NotificationsSettingsComponent,
              ),
          },
          {
            path: 'integrations',
            loadComponent: () =>
              import('./features/dashboard/settings/panels/integrations/integrations').then(
                (m) => m.IntegrationsSettingsComponent,
              ),
          },
          {
            path: 'danger-zone',
            loadComponent: () =>
              import('./features/dashboard/settings/panels/danger-zone/danger-zone').then(
                (m) => m.DangerZoneComponent,
              ),
          },
        ],
      },
    ],
  },
];
