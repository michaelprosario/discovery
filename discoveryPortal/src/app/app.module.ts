import { NgModule, importProvidersFrom } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideFirebaseApp, initializeApp } from '@angular/fire/app';
import { provideAuth, getAuth } from '@angular/fire/auth';

import { AppComponent } from './app';
import { routes } from './app.routes';
import { SideMenu } from './side-menu/side-menu';
import { NotebookExampleComponent } from "./examples/notebook-example.component";
import { NotebookList } from "./notebook-list/notebook-list";
import { UserMenuComponent } from './shared/user-menu/user-menu.component';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { environment } from '../environments/environment';


@NgModule({
  declarations: [
    AppComponent, SideMenu
  ],
  imports: [
    BrowserModule,
    CommonModule,
    RouterModule.forRoot(routes),
    NotebookExampleComponent,
    NotebookList,
    UserMenuComponent
],
  providers: [
    provideHttpClient(
      withInterceptors([authInterceptor])
    ),
    provideFirebaseApp(() => initializeApp(environment.firebase)),
    provideAuth(() => getAuth())
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
