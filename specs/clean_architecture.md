The Clean Architecture rules advocated by **Steve Smith (Ardalis)** and commonly applied in his reference solutions (often built on ASP.NET Core) are heavily guided by the **Dependency Inversion Principle (DIP)**.

The core idea is to keep the central business logic independent of external technologies (UI, database, etc.).

## Core Clean Architecture Rules (Ardalis/Smith)

| Rule Category | Common Clean Architecture Rules (Ardalis/Smith) |
| :--- | :--- |
| **Dependency Rule** | **Dependencies point inward** towards the Core project. The inner projects (Core) must not know about the outer projects (Infrastructure, Web). |
| **Project Structure** | The architecture is structured into **concentric layers** or projects: **Core** (innermost), **Infrastructure**, and **Web/UI** (outermost). |
| **Core Independence** | The **Core** project is the center of the solution and has **minimal dependencies**. It should have **zero direct dependencies** on external frameworks or the Infrastructure project. |
| **Interface Definition** | **Inner projects define interfaces (abstractions)**; **Outer projects implement them**. For instance, the Core project defines an `IRepository`, and the Infrastructure project implements it (e.g., `SqlRepository`). |
| **Infrastructure Role** | The **Infrastructure** project is where all **out-of-process concerns** reside, such as data access (Entity Framework, Dapper), external services (email, SMS), and file system access. |
| **Web/UI Role** | The **Web/UI** project's primary role is to handle external interaction, routing, and serialization, and to orchestrate the application by calling the core services. It **should not contain business logic**. |
| **Testability** | The design ensures **extreme testability** for the Core project, which contains the most important business logic, by isolating it from infrastructure dependencies. |

***

## Extended Rules

The additional rules you specified align perfectly with the goals of Clean Architecture and best practices for creating a maintainable, testable core:

### Structure and Responsibility

* **Core business logic belongs in core folder (or project):** This folder contains the **Domain Model** (Entities, Value Objects) and **Application Services/Use Cases** that orchestrate the domain logic.
* **Infrastructure elements belong in infra folder (or project):** This folder is dedicated to **implementation details** like concrete database access classes, external API clients, and logging setup.

### Dependency Management

* **Core folder should have minimal dependencies on external frameworks:** This is a fundamental rule (Framework Independent). It prevents the business logic from being tied to a specific technology like a web framework or ORM.
* **Core business logic services should depend upon providers and repositories:** Core services (e.g., Use Cases) should interact with data and external concerns only through **interfaces** (like `IRepository` or `IEventProvider`) defined in the Core itself.

### Service Design and Testing

* **Core business logic services should have unit tests:** The independence of the Core project makes its services easy to unit test without requiring external resources (like a database or file system).
* **Core services should always use command or query objects as method inputs:** This promotes the **Command Query Responsibility Segregation (CQRS)** pattern for application services, improving clarity and maintainability. A `Command` modifies state; a `Query` retrieves state.
* **Core services should always return an app result object that reports success, failure, and helpful messages and validation errors:** Using a dedicated `Result<T>` or `AppResult` object centralizes error handling and ensures services have a consistent, easy-to-consume signature, avoiding exceptions for expected business failures. This is a common pattern in robust, modern architectures.