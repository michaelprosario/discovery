import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app';
import { routes } from './app.routes';
import { SideMenu } from './side-menu/side-menu';
import { NotebookExampleComponent } from "./examples/notebook-example.component";
import { NotebookList } from "./notebook-list/notebook-list";


@NgModule({
  declarations: [
    AppComponent, SideMenu
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes),
    NotebookExampleComponent,
    NotebookList
],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
