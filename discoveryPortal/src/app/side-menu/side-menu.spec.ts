import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SideMenu } from './side-menu';

describe('SideMenu', () => {
  let component: SideMenu;
  let fixture: ComponentFixture<SideMenu>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SideMenu]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SideMenu);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
