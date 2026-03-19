param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

python -m econflow @Args

