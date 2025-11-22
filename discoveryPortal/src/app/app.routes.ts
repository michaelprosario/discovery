import { Routes } from '@angular/router';
import { EditNotebook } from './edit-notebook/edit-notebook';
import { NotebookList } from './notebook-list/notebook-list';
import { NewNotebook } from './new-notebook/new-notebook';
import { AddTextSource } from './add-text-source/add-text-source';
import { AddUrlSource } from './add-url-source/add-url-source';
import { AddPdfSource } from './add-pdf-source/add-pdf-source';

export const routes: Routes = [
    { path: '', component: NotebookList },
    { path: 'list-notebooks', component: NotebookList },    
    { path: 'edit-notebook/:id', component: EditNotebook },
    { path: 'edit-notebook/:id/add-text-source', component: AddTextSource },
    { path: 'edit-notebook/:id/add-url-source', component: AddUrlSource },
    { path: 'edit-notebook/:id/add-pdf-source', component: AddPdfSource },
    { path: 'new-notebook', component: NewNotebook }
];
