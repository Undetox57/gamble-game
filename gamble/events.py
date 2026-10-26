"""Random events. Each choice is (label, enabled(state) or None, effect(engine) -> (message, kind))."""
import math


def build_events():
    events = []

    def add(key, title, text, choices, cond=None):
        events.append({'key': key, 'title': title, 'text': text, 'choices': choices,
                       'cond': cond or (lambda s: True)})

    # --- an old friend
    add('friend', 'An old friend',
        'An old friend shows up at your door. He needs 100 TL until payday.',
        [('Lend him 100 TL', lambda s: s.balance >= 100,
          lambda a: ('You helped him out. ' + a.change(money=-100, mental=8, exp=5), 'win')),
         ('Say you are broke', None,
          lambda a: ('You feel a little guilty. ' + a.change(mental=-3), 'loss'))])

    # --- found wallet
    add('wallet', 'Found wallet', 'You find a wallet on the street. There is 150 TL inside, and an ID card.',
        [('Keep the cash', None,
          lambda a: ('Finders keepers... ' + a.change(money=150, mental=-6), 'info')),
         ('Return it to the owner', None,
          lambda a: ('The owner is thrilled and gives you a reward. ' + a.change(money=30, mental=5, exp=10), 'win'))])

    # --- underground betting ring
    def ring_join(a):
        a.state.no_gamble_days = 0
        if a.rng.random() < 0.4:
            return 'You won the side bet! ' + a.change(money=150), 'win'
        return 'You lost the side bet. ' + a.change(money=-100), 'loss'

    def ring_leave(a):
        a.state.no_gamble_days += 1
        a.check_clean_reward()
        return 'You walk away from the temptation. ' + a.change(mental=2), 'win'

    add('ring', 'Underground betting ring',
        'A guy in an alley offers you a spot in a private game. Risk 100 TL for a 40% chance at 150 TL.',
        [('Join in', lambda s: s.balance >= 100, ring_join), ('Walk away', None, ring_leave)],
        cond=lambda s: s.level >= 2)

    # --- VIP invitation
    def vip_accept(a):
        a.state.no_gamble_days = 0
        return 'The chips are free, but the hook is real. ' + a.change(money=120), 'info'

    add('vip', 'VIP invitation',
        'The casino sends you a VIP invitation with 120 TL in free chips. Accepting resets your no-gamble streak.',
        [('Accept the free chips', None, vip_accept),
         ('Decline', None, lambda a: ('You tear up the invitation. ' + a.change(mental=3), 'win'))],
        cond=lambda s: s.level >= 3)

    # --- unexpected bill
    add('bill', 'Unexpected bill', 'An unexpected bill arrives: 60 TL for something you completely forgot about.',
        [('Pay it', lambda s: s.balance >= 60, lambda a: ('Paid. ' + a.change(money=-60), 'info')),
         ('Ignore it', None,
          lambda a: ('It gets added to your debt. ' + a.change(debt=90, mental=-2), 'loss'))])

    # --- loved one
    def call_together(a):
        a.state.out_days = max(a.state.out_days, 3)
        return 'A lovely evening. You are protected from mental health loss for a few days. ' + \
               a.change(mental=6), 'win'

    add('call', 'A call from your loved one', 'Your loved one calls and asks if you want to spend the evening together.',
        [('Spend the evening together', None, call_together),
         ('Ignore the call', None, lambda a: ('You feel awful afterwards. ' + a.change(mental=-4), 'loss'))])

    # --- bank error
    add('bank_error', 'Bank error', 'The bank accidentally deposited 100 TL extra into your account.',
        [('Keep it', None, lambda a: ('Nobody noticed. ' + a.change(bank=100, mental=-3), 'info')),
         ('Report the error', None,
          lambda a: ('The bank thanks you for your honesty. ' + a.change(mental=3, exp=10), 'win'))])

    # --- tax audit
    def tax_pay(a, mult=1):
        fine = max(50, a.state.balance // 10) * mult
        short = a.pay(fine)
        return f'You owe {fine:,} TL.' + (f' {short:,} TL was added to your debt.' if short else '') + ' ', 'loss'

    def tax_fight(a):
        if a.rng.random() < 0.5:
            return 'Your lawyer pulls it off. Case dismissed. ' + a.change(mental=-2), 'win'
        msg, kind = tax_pay(a, 2)
        return 'You lost the appeal. ' + msg + a.change(mental=-4), kind

    add('tax', 'Tax audit', 'A tax inspector claims you owe a fine of 10% of your wallet (min 50 TL).',
        [('Pay the fine', None, lambda a: (lambda r: (r[0] + a.change(mental=-1), r[1]))(tax_pay(a))),
         ('Fight it (50%: dismissed, 50%: double fine)', None, tax_fight)],
        cond=lambda s: s.level >= 4)

    # --- support meeting
    def meeting_attend(a):
        a.state.no_gamble_days += 2
        a.check_clean_reward()
        return 'You listen to other people\'s stories and feel less alone. ' + a.change(mental=12), 'win'

    add('meeting', 'A flyer', 'You find a flyer for a local support group for people who gamble too much.',
        [('Attend the meeting', None, meeting_attend),
         ('Throw it away', None, lambda a: ('You toss it in the bin. Nothing changes.', 'info'))])

    # --- debt collector
    def collector_pay(a):
        amt = max(1, math.ceil(a.state.debt * 0.25))
        a.state.balance -= amt
        a.state.debt -= amt
        return f'You paid {amt:,} TL toward your debt. ' + a.change(mental=3), 'win'

    add('collector', 'Debt collector',
        'A debt collector knocks on your door. He wants 25% of your debt right now.',
        [('Pay 25% of your debt', lambda s: s.balance >= max(1, math.ceil(s.debt * 0.25)), collector_pay),
         ('Hide until he leaves', None, lambda a: ('Your heart is pounding. ' + a.change(mental=-8), 'loss'))],
        cond=lambda s: s.debt > 0)

    # --- overtime
    add('overtime', 'Overtime offer', 'Your boss offers you a night of overtime: 100 TL extra.',
        [('Take the overtime', None, lambda a: ('You are exhausted, but richer. ' + a.change(money=100, mental=-5), 'info')),
         ('Decline', None, lambda a: ('You get a good night\'s sleep.', 'info'))])

    # --- party
    add('party', 'Party invitation', 'Some friends invite you to a party. It costs 50 TL to get in.',
        [('Go (-50 TL)', lambda s: s.balance >= 50,
          lambda a: ('You had a great time. ' + a.change(money=-50, mental=8), 'win')),
         ('Stay home', None, lambda a: ('A quiet night in.', 'info'))])

    # --- tip
    def tip_buy(a):
        if a.rng.random() < 0.25:
            return 'The tip pays off! ' + a.change(money=150), 'win'
        return 'The tip was garbage. ' + a.change(money=-50), 'loss'

    add('tip', 'A "sure thing"', 'A stranger sells you a "sure thing" tip for tomorrow\'s race for 50 TL.',
        [('Buy the tip', lambda s: s.balance >= 50, tip_buy), ('Ignore him', None,
                                                                lambda a: ('Probably wise.', 'info'))],
        cond=lambda s: s.level >= 2)

    # --- attic
    add('attic', 'Old stuff', 'You find a box of old stuff in the attic.',
        [('Sell it all', None, lambda a: ('A neighbour buys everything. ' + a.change(money=80), 'win')),
         ('Keep it', None, lambda a: ('Old memories. ' + a.change(mental=2), 'info'))])
    return events
