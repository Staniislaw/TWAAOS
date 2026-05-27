import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyRegistrations } from './my-registrations';

describe('MyRegistrations', () => {
  let component: MyRegistrations;
  let fixture: ComponentFixture<MyRegistrations>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyRegistrations],
    }).compileComponents();

    fixture = TestBed.createComponent(MyRegistrations);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
