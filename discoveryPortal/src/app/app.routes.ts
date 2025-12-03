import { Routes } from '@angular/router';
import { EditNotebook } from './edit-notebook/edit-notebook';
import { NotebookList } from './notebook-list/notebook-list';
import { NewNotebook } from './new-notebook/new-notebook';
import { AddTextSource } from './add-text-source/add-text-source';
import { AddUrlSource } from './add-url-source/add-url-source';
import { AddPdfSource } from './add-pdf-source/add-pdf-source';
import { SyncNotebook } from './sync-notebook/sync-notebook';
import { NewBlogPost } from './new-blog-post/new-blog-post';
import { NotebookOutputs } from './notebook-outputs/notebook-outputs';
import { ViewOutput } from './view-output/view-output';
import { NewMindMap } from './new-mindmap/new-mindmap';
import { ChatComponent } from './chat/chat';
import { authGuard, noAuthGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    // Public routes
    {
        path: 'login',
        loadComponent: () => import('./auth/login/login.component').then(m => m.LoginComponent),
        canActivate: [noAuthGuard]
    },
    
    // Protected routes
    { path: '', component: NotebookList, canActivate: [authGuard] },
    { path: 'list-notebooks', component: NotebookList, canActivate: [authGuard] },    
    { path: 'edit-notebook/:id', component: EditNotebook, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/add-text-source', component: AddTextSource, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/add-url-source', component: AddUrlSource, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/add-pdf-source', component: AddPdfSource, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/sync', component: SyncNotebook, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/new-blog-post', component: NewBlogPost, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/new-mindmap', component: NewMindMap, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/outputs', component: NotebookOutputs, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/outputs/:outputId', component: ViewOutput, canActivate: [authGuard] },
    { path: 'edit-notebook/:id/chat', component: ChatComponent, canActivate: [authGuard] },
    { path: 'new-notebook', component: NewNotebook, canActivate: [authGuard] }
];
