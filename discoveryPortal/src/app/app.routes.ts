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

export const routes: Routes = [
    { path: '', component: NotebookList },
    { path: 'list-notebooks', component: NotebookList },    
    { path: 'edit-notebook/:id', component: EditNotebook },
    { path: 'edit-notebook/:id/add-text-source', component: AddTextSource },
    { path: 'edit-notebook/:id/add-url-source', component: AddUrlSource },
    { path: 'edit-notebook/:id/add-pdf-source', component: AddPdfSource },
    { path: 'edit-notebook/:id/sync', component: SyncNotebook },
    { path: 'edit-notebook/:id/new-blog-post', component: NewBlogPost },
    { path: 'edit-notebook/:id/new-mindmap', component: NewMindMap },
    { path: 'edit-notebook/:id/outputs', component: NotebookOutputs },
    { path: 'edit-notebook/:id/outputs/:outputId', component: ViewOutput },
    { path: 'new-notebook', component: NewNotebook }
];
