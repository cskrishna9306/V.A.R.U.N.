def split_equally(total: float, n: int) -> list[float]:
    """
    Split total dollars into n equal parts; returned values sum exactly to total.
    This helper function ensures that the total sum of the shares equals the total amount and redistributes the remainder cents to the recipients.
    """
    if n <= 0:
        raise ValueError("The total # of recipients must be positive")
    
    # Convert the total to cents and split equally
    total_cents = int(round(total * 100))
    base_cents = total_cents // n
    remainder_cents = total_cents % n

    # Return the list of equal shares w/ remainder distribution
    return [
        (base_cents + (1 if i < remainder_cents else 0)) / 100.0
        for i in range(n)
    ]