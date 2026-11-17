import { render, screen } from '@testing-library/react';
import { it, expect, vi } from 'vitest';
import { Application } from '../App';
import { GeometricMesh } from '../strata';

it('offers only provisioned FastAPI authentication under the MeritLatch identity', () => {
  history.replaceState({},'', '/login');
  render(<Application />);
  expect(screen.getByRole('heading',{name:'Welcome back'})).toBeVisible();
  expect(screen.getByText('MeritLatch',{exact:true})).toBeVisible();
  expect(screen.getByLabelText('Tenant')).toBeRequired();
  expect(screen.getByLabelText('Username')).toBeRequired();
  expect(screen.getByLabelText('Password')).toHaveAttribute('type','password');
  expect(screen.getAllByRole('button')).toHaveLength(1);
  expect(screen.queryByRole('button',{name:/Google|GitHub|SSO|magic|reset|register/i})).toBeNull();
  expect(screen.getByText('LOCAL DEMO · MOCK_AI')).toBeVisible();
});

it('keeps geometric decoration outside the interactive or accessibility tree', () => {
  const timer=vi.spyOn(window,'setInterval');
  const {container}=render(<GeometricMesh />);
  const mesh=container.querySelector('svg')!;
  expect(mesh).toHaveAttribute('aria-hidden','true');
  expect(mesh).toHaveAttribute('focusable','false');
  expect(mesh.querySelectorAll('circle')).toHaveLength(26);
  expect(container.querySelectorAll('button,input,a,canvas')).toHaveLength(0);
  expect(timer).not.toHaveBeenCalled();
  timer.mockRestore();
});
