
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a9541da0b7241707b1b0f5f757484611 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0aa67dc779c692a1aecd12536af7a26c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "20px", ["color"] : "#4e4e6a", ["cursor"] : "pointer", ["&:hover"] : ({ ["color"] : "#f0f0fa" }) }),onClick:on_click_0aa67dc779c692a1aecd12536af7a26c},children)
    )
});
