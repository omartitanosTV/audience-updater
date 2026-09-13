from django import forms


WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class AudienceForm(forms.Form):
    """Form used to create and edit one audience configuration."""

    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={"placeholder": "e.g. Sports - Titan OS - ES"}
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "What this audience represents"}
        ),
    )
    query = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 16,
                "class": "sql-input",
                "placeholder": "SELECT ...",
            }
        ),
    )
    mode = forms.ChoiceField(
        choices=[
            ("replace", "Replace"),
            ("append", "Append"),
        ],
    )
    refresh_frequency = forms.ChoiceField(
        choices=[
            ("manual", "Manual"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("once", "One-time test"),
        ],
        initial="weekly",
    )
    weekly_day = forms.TypedChoiceField(
        choices=WEEKDAY_CHOICES,
        coerce=int,
        initial=0,
        required=False,
    )
    monthly_day = forms.IntegerField(
        min_value=1,
        max_value=31,
        initial=1,
        required=False,
    )
    schedule_time = forms.TimeField(
        initial="22:00",
        widget=forms.TimeInput(
            format="%H:%M",
            attrs={"type": "time"},
        ),
    )
    once_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )
    enabled = forms.BooleanField(
        required=False,
        initial=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get("refresh_frequency")

        if frequency == "weekly" and cleaned_data.get("weekly_day") is None:
            self.add_error(
                "weekly_day",
                "Choose a weekday for a weekly refresh.",
            )

        if frequency == "monthly" and cleaned_data.get("monthly_day") is None:
            self.add_error(
                "monthly_day",
                "Choose a day of the month.",
            )

        if frequency == "once" and cleaned_data.get("once_at") is None:
            self.add_error(
                "once_at",
                "Choose a date and time for the one-time test.",
            )

        return cleaned_data
