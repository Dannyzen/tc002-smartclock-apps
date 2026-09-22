# @name Birthday Countdown
# @desc A persistent on-Clock birthday countdown. Recalculates after midnight.
# @config person text "Person" default="Birthday" maxlen=18
# @config birthMonth number "Birth month" default=1 min=1 max=12 step=1
# @config birthDay number "Birth day" default=1 min=1 max=31 step=1
# @config color color "Color" default=#00E5FF
# @config leapDay select "Feb. 29 in non-leap years" default=feb28 options=feb28,mar1
# @config dwellMs number "Card dwell" default=6000 min=1000 max=30000 step=500 unit=ms

class BirthdayCountdown
  var days_left
  var date_key

  def init()
    self.days_left = nil
    self.date_key = ""
  end

  def is_leap(candidate_year)
    return candidate_year % 400 == 0 || (candidate_year % 4 == 0 && candidate_year % 100 != 0)
  end

  def days_in_month(candidate_year, candidate_month)
    if candidate_month == 2
      if self.is_leap(candidate_year)
        return 29
      end
      return 28
    end
    if candidate_month == 4 || candidate_month == 6 || candidate_month == 9 || candidate_month == 11
      return 30
    end
    return 31
  end

  def is_birthday(candidate_year, candidate_month, candidate_day)
    var target_month = num(store.get("birthMonth"))
    var target_day = num(store.get("birthDay"))
    # Feb. 29 is valid input even when this candidate year has only 28 days.
    # Resolve its chosen non-leap observance before the generic validity guard.
    if target_month == 2 && target_day == 29 && !self.is_leap(candidate_year)
      if store.get("leapDay") == "mar1"
        return candidate_month == 3 && candidate_day == 1
      end
      return candidate_month == 2 && candidate_day == 28
    end
    # A manually configured impossible date, such as April 31, is not a birthday.
    if target_day > self.days_in_month(candidate_year, target_month)
      return false
    end
    return candidate_month == target_month && candidate_day == target_day
  end

  def calculate_days_left()
    var candidate_year = year()
    var candidate_month = month()
    var candidate_day = day()
    if candidate_year < 0
      return nil
    end
    var remaining = 0
    while remaining <= 366
      if self.is_birthday(candidate_year, candidate_month, candidate_day)
        return remaining
      end
      candidate_day += 1
      remaining += 1
      if candidate_day > self.days_in_month(candidate_year, candidate_month)
        candidate_day = 1
        candidate_month += 1
        if candidate_month > 12
          candidate_month = 1
          candidate_year += 1
        end
      end
    end
    return nil
  end

  def refresh()
    if year() < 0
      return
    end
    self.date_key = str(year()) + "-" + str(month()) + "-" + str(day())
    self.days_left = self.calculate_days_left()
  end

  def loop()
    if year() < 0
      return
    end
    var current_key = str(year()) + "-" + str(month()) + "-" + str(day())
    if self.date_key != current_key
      self.refresh()
    end
  end

  def should_show()
    return self.days_left != nil
  end

  def duration()
    return store.get("dwellMs")
  end

  def centered(label, tint)
    var label_width = text_ink_width(label)
    text((width() - label_width) / 2, height() - 2, label, tint)
  end

  def draw()
    if self.days_left == nil
      self.refresh()
    end
    clear()
    if self.days_left == nil
      self.centered("DATE?", 0xFF0000)
      return
    end
    var tint = store.get("color")
    if self.days_left == 0
      self.centered("TODAY!", tint)
    elif second() % 6 < 3
      self.centered(store.get("person"), tint)
    else
      self.centered(str(self.days_left) + " DAYS", tint)
    end
  end
end

return BirthdayCountdown()
