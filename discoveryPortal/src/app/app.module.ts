import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app';
import { routes } from './app.routes';
import { SideMenu } from './side-menu/side-menu';


@NgModule({
  declarations: [
    AppComponent, SideMenu
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
