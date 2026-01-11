When working with components in this directory:

- Create a new database model in a separate module
- Use predefined mixins if metadata like created_at, created_by etc are requested for a module
- Try to create two levels for model: 
    SomeModelNameBase which inherits SqlModelBase and SomeModelNameModel which extends SomeModelNameBase and some metadata if requested
    Follow healthcheck.py as an example
- table names MUST be with a plural format. For example, like in healthcheck.py
- If the table has enum, create two classes: 
    SomeEnumType which extends EnumString from types.py
    SomeEnumTypeString which extends EnumString
    a column must be defined as "type: SomeEnumType = sm.Field(sa_type=SomeEnumTypeString)". In any problem, follow healthcheck.py as a hint