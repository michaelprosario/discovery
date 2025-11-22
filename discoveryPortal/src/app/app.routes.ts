import { Routes } from '@angular/router';
import { EditNotebook } from './edit-notebook/edit-notebook';
import { NotebookList } from './notebook-list/notebook-list';
import { NewNotebook } from './new-notebook/new-notebook';
import { AddTextSource } from './add-text-source/add-text-source';

export const routes: Routes = [
    { path: '', component: NotebookList },
    { path: 'list-notebooks', component: NotebookList },    
    { path: 'edit-notebook/:id', component: EditNotebook },
    { path: 'edit-notebook/:id/add-text-source', component: AddTextSource },
    { path: 'new-notebook', component: NewNotebook }
];
