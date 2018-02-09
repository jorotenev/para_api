# Endpoints
`/expenses_api/<api version>`
## v1
All endpoints expect a x-firebase-auth header with the firebase auth token as a value.

* **GET** `/get_expenses_list?start_id=<int>&batch_size=<int>&sort_by=<str>`
  *  parameters
     * `?start_id` - id, of the same type as the id type of the app (`export type ExpenseIdType`). there isn't necesserily an actual expense with this id on the server (e.g. it might have been deleted) but the search will start from this id. Optional. If omitted, the other parameters will be used to determine the first expense in the response.
     * `?batch_size` - the __maximum__ size of the response. Optional. Default 10
     * `?sort_by` - one of `["date_descending"|"date_ascending"]`. Optional. Default `"date_descending`
  * `200` on successfull response
    ```
    [ {<Expense Object>}* ]
    ``` 
  * 400 on malformed request
    ```{error: "<reason>"}```
   
* __GET__ `/get_expense_by_id/<int>`
  * `200` on expense found
  ```{<Expense object>}```
  * `404` on expense not found or if not authorized
  ```{error: "<not found | not authorized>"}```
* __POST__ `/persist`
  * payload: `{<Expense Object with id=null>}`
  * 200 on expense persisted
  `{<Expense object>}`
  * 400 on expense not processable
  `{error: "<reason>"}`
* __PUT__ `/update`
  * payload `{<Expense object>}`
  * `200` on expense updated
    `{<Expense object>}`
  * `400` on expense not processible (invalid expense)
  `{error: "<reason>"}`
  * `404` on expense with such id not found or not authorized to update this expense
  `{error: "<reason>"}`
* __DELETE__ `/remove`
  * payload `{id: <int>}`
  * response
    * `200` on successful deletion
    * `404` if no such expense / not authorized to delete this expense
  `{msg: "<reason>"}`