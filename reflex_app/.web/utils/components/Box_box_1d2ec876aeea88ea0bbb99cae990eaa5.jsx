
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_1d2ec876aeea88ea0bbb99cae990eaa5 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a5fd45cc004314db8ee0f75ba879ae32 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.logout", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a", ["cursor"] : "pointer", ["&:hover"] : ({ ["color"] : "#8282a2" }) }),onClick:on_click_a5fd45cc004314db8ee0f75ba879ae32},children)
    )
});
