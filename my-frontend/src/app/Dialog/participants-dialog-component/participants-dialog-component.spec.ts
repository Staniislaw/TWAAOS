import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParticipantsDialogComponent } from './participants-dialog-component';

describe('ParticipantsDialogComponent', () => {
  let component: ParticipantsDialogComponent;
  let fixture: ComponentFixture<ParticipantsDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParticipantsDialogComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParticipantsDialogComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
