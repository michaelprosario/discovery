11/15

Given
- I am adding a content source via url via the web interface
- url: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHHDRHWr11fR74NZ5swzuCOLRsfPpYAWyM9lj0A12O7Lujnt82q5U8xFNjy_6IEZ1UZ1JtDPKJgH9gHMnzRIsFQx5HnIT9tU569_6x6MEqtV-SKZmMMKzheNumNaloPegoZhYdFek7xaA9C8BXOfQ==

When the following api executes at /api/sources/url
Then the system reports the following response:

{
    "detail": {
        "error": "Failed to fetch URL: Failed to fetch article: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters"
    }
}

Fix bug
===

Given
- I am adding a content source via url: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHhKzyQZ1pWcJbvyLBZ3fxadyxG6ykmDinxC_13N5_l8dsk3d27SXWpLrrm5J_4FhC_f20h51Yfkx--ronLwWEdSofKwdn6k89hl8LboRQQl-B7rCXnluW46FGT_An63GWIrK6qDfUWGt_26ewMWW4=

I get error:
Error: Failed to fetch URL: Page not found (404): https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHhKzyQZ1pWcJbvyLBZ3fxadyxG6ykmDinxC_13N5_l8dsk3d27SXWpLrrm5J_4FhC_f20h51Yfkx--ronLwWEdSofKwdn6k89hl8LboRQQl-B7rCXnluW46FGT_An63GWIrK6qDfUWGt_26ewMWW4=

===

Given
- I am adding a content source via url: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_Orvv_lhoPKAWycSuHcJ8DeP4GJXkM5WnjQ09FjC45Leo95XzLCi3XbgdGW42oL5reqgchmy-PAxBRpC7cBUp5qszz8UrCJGwuljYzXuMOJiHvtjWE6kJMupzmhA5Esg44Pon8JVTwd4bVXCOpDwhCZi6DG0yeBpdxtnBRnLoYEU-z-6XONQcjzaLVv7RBm-ekyVd
- I get the following error: Error: Failed to fetch URL: No text content extracted from article

====


