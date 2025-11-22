import { Component, ChangeDetectorRef } from '@angular/core';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { ListNotebooksParams, NotebookResponse } from '../core/models/notebook.models';
import { CommonModule } from '@angular/common';
import { lastValueFrom } from 'rxjs';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-notebook-list',
  imports: [CommonModule, LoadingComponent],
  templateUrl: './notebook-list.html',
  styleUrl: './notebook-list.scss',
})
export class NotebookList {


  records: NotebookResponse[] = [];
  screenLoaded: boolean = false;
  constructor(
    private dataService: NotebookApiService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef) {
  }

  async ngOnInit(): Promise<void> {

    const query = {} as ListNotebooksParams;
    query.sort_by = 'name';
    query.sort_order = 'asc';

    try {
      const getListResponse = await lastValueFrom(this.dataService.listNotebooks(query));
      console.log(getListResponse);
      if (getListResponse) {
        this.records = getListResponse.notebooks;
        this.screenLoaded = true;
        this.cdr.detectChanges();
      } else {
        alert('ngOnInit / get notebooks list failed');
        console.log(getListResponse);
      }
    } catch (error) {
      console.error('Error loading notebooks', error);
      alert('Error loading notebooks');
    }
  }

  onEditRecord(record: NotebookResponse){
    this.router.navigate(['/edit-notebook/' + record.id]);
  }

  onNewRecord(){
    this.router.navigate(['/new-notebook']);
  }

}
