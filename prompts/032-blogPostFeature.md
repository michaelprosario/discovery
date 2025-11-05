- follow specs/clean_architecture.md
- follow specs/core_stories.md
- As a user, I should be able to open a notebook record in the application and generate a blog post based on a prompt and content sources. Do not create a jupyter notebook.  Blog post should be around 500 to 600 words.  Please include reference links or titles at the bottom of the blog post.

=== 

In the menu for a notebook, add an option to generate a blog post.


===

when I do a blog post generation, I observe an error:

{
"detail": {
"error": "Blog generation failed: 'str' object has no attribute 'value'"
}
}

====

on the generate blog post screen, after creating a blog post.. I should still have the ability to re-generate content

====
Given
- I have opened a notebook
- I have linked a source to the notebook with valid data
- I have ingested the source into my vector database
- I have started the "generate blog post" screen
- I have filled out valid inputs

When 
- I click "save blog post"

Then
- I should not receive an error.

app.js:1574  Save error: TypeError: this.loadNotebook is not a function
    at DiscoveryApp.saveBlogPost (app.js:1571:28)
    at HTMLButtonElement.<anonymous> (app.js:81:89)

====
- Explore ux files here: src/api/static
- On the discovery notebook screen, I should see a list of outputs that have been generated for the notebook. ( blog posts and future data types)  
    - I should be able to download the output.  (text)
    - I should be able to delete the output(please add confirm for delete)  
    - I should be able to view the output
