import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthCallbackComponent } from './auth-callback-component';

describe('AuthCallbackComponent', () => {
  let component: AuthCallbackComponent;
  let fixture: ComponentFixture<AuthCallbackComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthCallbackComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthCallbackComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
